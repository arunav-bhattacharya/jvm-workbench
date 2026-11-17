package workbench.patterns.l06;

import java.util.List;

/** Notices (what to say) and channels (how it travels) vary on their own: 2 + 2 classes, not 2 x 2. */
public class BridgeDemo {
    // the implementor side: how a message travels
    interface Channel { String deliver(String to, String body); }
    record Sms() implements Channel {
        public String deliver(String to, String body) { return "SMS   to " + to + ": " + body; }
    }
    record Email() implements Channel {
        public String deliver(String to, String body) { return "EMAIL to " + to + ": " + body; }
    }

    // the abstraction side: what to say. Each notice HOLDS a channel instead of being one.
    sealed interface Notice permits OnItsWay, SoldOut {
        Channel channel();
        String send(String to);
    }
    record OnItsWay(Channel channel, String orderNo, String courier) implements Notice {
        public String send(String to) { return channel.deliver(to, "order " + orderNo + " is on its way with " + courier); }
    }
    record SoldOut(Channel channel, String item, int days) implements Notice {
        public String send(String to) { return channel.deliver(to, item + " is sold out, back in " + days + " days"); }
    }

    public static void main(String[] args) {
        List<Channel> channels = List.of(new Sms(), new Email());
        for (Channel ch : channels) {
            System.out.println(new OnItsWay(ch, "7781", "Pedal Post").send("Ana"));
            System.out.println(new SoldOut(ch, "rye bread", 2).send("Ben"));
        }
    }
}
