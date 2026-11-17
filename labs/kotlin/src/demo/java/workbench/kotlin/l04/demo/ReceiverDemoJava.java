package workbench.kotlin.l04.demo;

import kotlin.Unit;

import java.util.function.Consumer;

/**
 * Java twin of ReceiverDemo.kt. Java has no lambdas with receivers. A Kotlin
 * StringBuilder.() -> Unit is a Function1<StringBuilder, Unit> to Java: the receiver is the first parameter.
 */
public class ReceiverDemoJava {

    // Java's own idiom for the same job: a Consumer that gets the builder as a parameter
    static String ticketJava(Consumer<StringBuilder> block) {
        StringBuilder sb = new StringBuilder();
        block.accept(sb);
        return sb.toString();
    }

    public static void main(String[] args) {
        String t = ReceiverDemoKt.ticket(sb -> {
            sb.append("flyer.pdf x ").append(250);
            return Unit.INSTANCE;                     // Kotlin's Unit is a real object here
        });
        System.out.println(t);
        System.out.println(ticketJava(sb -> sb.append("menu.pdf x ").append(40)));

        StringBuilder sb = new StringBuilder();
        ReceiverDemoKt.getWithReceiver().invoke(sb);  // a receiver lambda, invoked with the receiver as argument
        System.out.println(sb);
    }
}
