package workbench.patterns.l02;

import java.util.function.Supplier;

/** A factory method over a sealed family, and the same factory passed around as a function. */
public class MessengerFactory {
    enum Channel { SMS, EMAIL, FAKE }

    sealed interface Messenger permits SmsMessenger, EmailMessenger, FakeMessenger {
        String send(String to, String text);

        // the static factory: an exhaustive switch over the enum, with no default branch
        static Messenger of(Channel c) {
            return switch (c) {
                case SMS -> new SmsMessenger();
                case EMAIL -> new EmailMessenger();
                case FAKE -> new FakeMessenger();
            };
        }
    }

    record SmsMessenger() implements Messenger {
        public String send(String to, String text) { return "sms to " + to + ": " + text; }
    }
    record EmailMessenger() implements Messenger {
        public String send(String to, String text) { return "email to " + to + ": " + text; }
    }
    record FakeMessenger() implements Messenger {
        public String send(String to, String text) { return "fake: nothing sent"; }
    }

    // the modern "factory method": the caller hands in how to make the product
    record OrderNotices(Supplier<? extends Messenger> messengers) {
        String orderLeft(String customer) { return messengers.get().send(customer, "your order is on its way"); }
    }

    public static void main(String[] args) {
        for (Channel c : Channel.values()) {
            System.out.println(c + " -> " + Messenger.of(c).send("anna", "your order is on its way"));
        }
        System.out.println("test notices -> " + new OrderNotices(FakeMessenger::new).orderLeft("anna"));
    }
}
