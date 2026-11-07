package workbench.patterns.l06;

import java.util.List;

/** Alerts (what happened) and channels (how it travels) vary on their own: 2 + 2 classes, not 2 x 2. */
public class BridgeDemo {
    // the implementor side: how a message travels
    interface Channel { String deliver(String to, String body); }
    record Sms() implements Channel {
        public String deliver(String to, String body) { return "SMS   to " + to + ": " + body; }
    }
    record Email() implements Channel {
        public String deliver(String to, String body) { return "EMAIL to " + to + ": " + body; }
    }

    // the abstraction side: what happened. Each alert HOLDS a channel instead of being one.
    sealed interface Alert permits PaymentFailed, FraudSuspected {
        Channel channel();
        String raise(String to);
    }
    record PaymentFailed(Channel channel, String paymentId, String reason) implements Alert {
        public String raise(String to) { return channel.deliver(to, "payment " + paymentId + " failed: " + reason); }
    }
    record FraudSuspected(Channel channel, String last4, int score) implements Alert {
        public String raise(String to) { return channel.deliver(to, "card ****" + last4 + " flagged, risk " + score); }
    }

    public static void main(String[] args) {
        List<Channel> channels = List.of(new Sms(), new Email());
        for (Channel ch : channels) {
            System.out.println(new PaymentFailed(ch, "pay_881", "issuer declined (51)").raise("on-call"));
            System.out.println(new FraudSuspected(ch, "4242", 91).raise("risk-team"));
        }
    }
}
