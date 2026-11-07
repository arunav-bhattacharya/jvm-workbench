package workbench.events.l03.demo.javaview;

import kotlin.jvm.JvmClassMappingKt;

/** Java calling the Kotlin API in JavaViewApi.kt. */
public class JavaViewDemo {
    public static void main(String[] args) {
        // What works, and why
        PlainBus plain = new PlainBus();                         // all parameters have defaults: Kotlin adds a no-arg constructor
        FriendlyBus friendly = new FriendlyBus("refunds");       // exists because of @JvmOverloads
        Registry.subscribe(PaymentCaptured.class,                // the Class overload, static because of @JvmStatic
                e -> System.out.println("java handler: " + Events.paymentId(e) + " " + Events.amountMinor(e)));
        Registry.INSTANCE.subscribe(JvmClassMappingKt.getKotlinClass(PaymentCaptured.class),   // the KClass one, the long way
                e -> System.out.println("via KClass:   " + e));
        Registry.INSTANCE.publish(Events.captured("pay_7781", 1_999));   // no @JvmStatic: Java goes through INSTANCE
        System.out.println(plain.getName() + ", " + friendly.getName());

        try {
            Events.captured("7781", 1_999);
        } catch (IllegalArgumentException e) {
            System.out.println("refused from Java: " + e.getMessage());
        }

        // Step 2: uncomment these one at a time, run, and read javac's error.
        // new PlainBus("refunds");
        // Registry.subscribe(e -> { });
        // new PaymentCaptured(new PaymentId("pay_7781"), new Money(1_999));
        // Registry.INSTANCE.describe("pay_7781");
    }
}
