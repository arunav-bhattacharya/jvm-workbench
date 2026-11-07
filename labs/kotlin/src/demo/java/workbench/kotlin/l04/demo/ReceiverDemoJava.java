package workbench.kotlin.l04.demo;

import kotlin.Unit;

import java.util.function.Consumer;

/**
 * Java twin of ReceiverDemo.kt. Java has no lambdas with receivers. A Kotlin
 * StringBuilder.() -> Unit is a Function1<StringBuilder, Unit> to Java: the receiver is the first parameter.
 */
public class ReceiverDemoJava {

    // Java's own idiom for the same job: a Consumer that gets the builder as a parameter
    static String receiptJava(Consumer<StringBuilder> block) {
        StringBuilder sb = new StringBuilder();
        block.accept(sb);
        return sb.toString();
    }

    public static void main(String[] args) {
        String r = ReceiverDemoKt.receipt(sb -> {
            sb.append("captured ").append(1_999);
            return Unit.INSTANCE;                     // Kotlin's Unit is a real object here
        });
        System.out.println(r);
        System.out.println(receiptJava(sb -> sb.append("refunded ").append(500)));

        StringBuilder sb = new StringBuilder();
        ReceiverDemoKt.getWithReceiver().invoke(sb);  // a receiver lambda, invoked with the receiver as argument
        System.out.println(sb);
    }
}
