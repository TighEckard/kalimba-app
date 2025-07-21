<?php
/**
 * Plugin Name: AI Reception Subscription Manager
 * Description: Handles subscription cancellation and Twilio number release.
 * Version: 1.0
 * Author: Your Name
 */

// Exit if accessed directly
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

// ********** STEP 2A: Save Subscription Data (Assumed Already Done) **********
// When a user subscribes via Stripe, you should store their subscription ID and Twilio number.
// For example, in your Stripe success handler:
// update_user_meta( $user_id, 'subscription_id', $stripe_subscription_id );
// update_user_meta( $user_id, 'twilio_number', $twilio_phone_number );

// ********** STEP 2B: Include Required Libraries **********
// Make sure the Twilio PHP SDK is loaded. If you use Composer, this might be done automatically.
// For example, if you’re not using Composer, include the Twilio autoload file:
// require_once( plugin_dir_path( __FILE__ ) . 'path/to/twilio-php/Services/Twilio.php' );

// ********** STEP 2C: Initialize Twilio Client and (optionally) Stripe Client **********
// Replace the placeholder values with your actual keys.
$twilio_account_sid = 'YOUR_TWILIO_ACCOUNT_SID';
$twilio_auth_token = 'YOUR_TWILIO_AUTH_TOKEN';
if ( ! class_exists( 'Twilio\Rest\Client' ) ) {
    // Adjust the path if needed.
    require_once( plugin_dir_path( __FILE__ ) . 'vendor/autoload.php' );
}
$twilio_client = new Twilio\Rest\Client( $twilio_account_sid, $twilio_auth_token );

// ********** STEP 2D: Create REST API Endpoint for Cancellation **********
add_action( 'rest_api_init', function() {
    register_rest_route( 'ai-reception/v1', '/cancel-subscription', array(
        'methods'  => 'POST',
        'callback' => 'cancel_subscription_and_twilio',
        'permission_callback' => function() {
            return is_user_logged_in();
        },
    ));
});

function cancel_subscription_and_twilio( WP_REST_Request $request ) {
    $user_id = get_current_user_id();
    if ( ! $user_id ) {
        return new WP_Error( 'unauthorized', 'Not logged in', array( 'status' => 401 ) );
    }
    
    // Retrieve subscription and Twilio number from user meta.
    $subscription_id = get_user_meta( $user_id, 'subscription_id', true );
    $twilio_number = get_user_meta( $user_id, 'twilio_number', true );
    
    // --- Cancel the Stripe Subscription ---
    // Replace this with your actual Stripe cancellation function.
    $stripe_cancellation = cancel_stripe_subscription( $subscription_id );
    if ( is_wp_error( $stripe_cancellation ) ) {
        return $stripe_cancellation;
    }
    
    // --- Release the Twilio Number ---
    try {
        // Search for the Twilio phone number resource.
        $numbers = $GLOBALS['twilio_client']->incoming_phone_numbers->read( array(
            "phoneNumber" => $twilio_number
        ) );
        if ( ! empty( $numbers ) ) {
            $numbers[0]->delete();
        }
    } catch ( Exception $e ) {
        return new WP_Error( 'twilio_error', $e->getMessage(), array( 'status' => 500 ) );
    }
    
    // Remove subscription and phone number meta.
    delete_user_meta( $user_id, 'subscription_id' );
    delete_user_meta( $user_id, 'twilio_number' );
    
    return new WP_REST_Response( array( 'success' => true, 'message' => 'Subscription and phone number canceled.' ), 200 );
}

// Dummy Stripe cancellation function – replace with real implementation.
function cancel_stripe_subscription( $subscription_id ) {
    // Example using the Stripe PHP library:
    // \Stripe\Stripe::setApiKey('YOUR_STRIPE_SECRET_KEY');
    // try {
    //     $subscription = \Stripe\Subscription::retrieve($subscription_id);
    //     $subscription->cancel();
    //     return true;
    // } catch (Exception $e) {
    //     return new WP_Error('stripe_error', $e->getMessage(), array('status' => 500));
    // }
    return true; // Dummy response for now.
}

// ********** STEP 2E: Create Shortcode for the Manage Subscription Page **********
function cancel_subscription_shortcode() {
    ob_start();
    ?>
    <div id="cancel-subscription-container" style="max-width: 400px; margin: 20px auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px; font-family: Arial, sans-serif;">
        <h2>Manage Your Subscription</h2>
        <button id="cancel-subscription-btn" style="background-color: #9a2da7; color: #fff; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; transition: background-color 0.2s ease, transform 0.2s ease; margin-top: 15px;">Cancel Subscription</button>
        <div id="cancel-feedback" style="margin-top: 10px; font-weight: bold;"></div>
    </div>
    <script>
        document.getElementById('cancel-subscription-btn').addEventListener('click', function() {
            if ( confirm("Are you sure you want to cancel your subscription?") ) {
                fetch('<?php echo esc_url( home_url( '/wp-json/ai-reception/v1/cancel-subscription' ) ); ?>', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-WP-Nonce': '<?php echo wp_create_nonce('wp_rest'); ?>'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('cancel-feedback').innerText = data.message;
                })
                .catch(error => {
                    document.getElementById('cancel-feedback').innerText = 'Error: ' + error.message;
                });
            }
        });
    </script>
    <?php
    return ob_get_clean();
}
add_shortcode( 'cancel_subscription', 'cancel_subscription_shortcode' );
