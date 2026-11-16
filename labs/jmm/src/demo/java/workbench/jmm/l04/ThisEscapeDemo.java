package workbench.jmm.l04;

/**
 * A constructor that starts a thread before it has finished setting its fields.
 * A heartbeat is a short "still running" message that one program sends another every few seconds.
 */
public class ThisEscapeDemo {
    static final class HeartbeatSender {
        private final String endpoint;

        HeartbeatSender(String endpointName) {
            Thread beat = new Thread(this::sendHeartbeat, "heartbeat");
            beat.start();                            // `this` escapes to another thread here...
            this.endpoint = resolve(endpointName);   // ...and this final field is set about 50 ms later
        }

        void sendHeartbeat() {
            System.out.println("heartbeat thread sends to: " + endpoint);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        HeartbeatSender sender = new HeartbeatSender("head-office");
        System.out.println("constructor finished, endpoint = " + sender.endpoint);
        Thread.sleep(100);
    }

    // stands in for a slow lookup of the address over the network
    static String resolve(String name) {
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return "https://" + name + ".example.com";
    }
}
