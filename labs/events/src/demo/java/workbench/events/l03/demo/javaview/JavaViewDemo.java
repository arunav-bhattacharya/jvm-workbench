package workbench.events.l03.demo.javaview;

import kotlin.jvm.JvmClassMappingKt;

/** Java calling the Kotlin API in JavaViewApi.kt. */
public class JavaViewDemo {
    public static void main(String[] args) {
        // What works, and why
        PlainBus plain = new PlainBus();                         // all parameters have defaults: Kotlin adds a no-arg constructor
        FriendlyBus friendly = new FriendlyBus("deliveries");    // exists because of @JvmOverloads
        Registry.subscribe(ParcelCollected.class,                // the Class overload, static because of @JvmStatic
                e -> System.out.println("java handler: " + Events.parcelId(e) + " " + Events.grams(e)));
        Registry.INSTANCE.subscribe(JvmClassMappingKt.getKotlinClass(ParcelCollected.class),   // the KClass one, the long way
                e -> System.out.println("via KClass:   " + e));
        Registry.INSTANCE.publish(Events.collected("PP-7781", 2_500));   // no @JvmStatic: Java goes through INSTANCE
        System.out.println(plain.getName() + ", " + friendly.getName());

        try {
            Events.collected("7781", 2_500);
        } catch (IllegalArgumentException e) {
            System.out.println("refused from Java: " + e.getMessage());
        }

        // Step 2: uncomment these one at a time, run, and read javac's error.
        // new PlainBus("deliveries");
        // Registry.subscribe(e -> { });
        // new ParcelCollected(new ParcelId("PP-7781"), new Weight(2_500));
        // Registry.INSTANCE.describe("PP-7781");
    }
}
