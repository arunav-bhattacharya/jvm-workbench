package workbench.kotlin.l05.demo;

import kotlin.Unit;

/**
 * Java twin of ContractsDemo.kt. Java has no contracts. It has no null checks in the type system to
 * satisfy, its instanceof pattern binds a new variable instead of smart-casting, and a lambda may
 * not assign a local variable at all.
 */
public class ContractsDemoJava {
    public static void main(String[] args) {
        String currency = ContractsDemoKt.lookupCurrency("m-981");
        ContractsDemoKt.requireCurrency(currency);              // to Java: a void method, nothing more
        System.out.println("currency = " + currency.toUpperCase());

        PaymentEvent event = new Captured("pay_7", 1_999);
        if (event instanceof Captured c) {                      // the pattern binds c: no promise needed
            System.out.println("captured " + c.getAmountMinor());
        }

        // String label; once(() -> { label = "x"; ... }) would not compile:
        // "local variables referenced from a lambda expression must be final or effectively final"
        String[] label = new String[1];
        ContractsDemoKt.once(() -> { label[0] = "batch-17"; return Unit.INSTANCE; });
        System.out.println("label = " + label[0]);
    }
}
