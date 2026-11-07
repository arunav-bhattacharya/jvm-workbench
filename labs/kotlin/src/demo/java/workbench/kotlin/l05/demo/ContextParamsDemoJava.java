package workbench.kotlin.l05.demo;

/**
 * Java twin of ContextParamsDemo.kt. Java has no context parameters. To Java they are ordinary
 * leading parameters: context parameters first, then the extension receiver, then the rest.
 */
public class ContextParamsDemoJava {
    public static void main(String[] args) {
        Logger console = System.out::println;
        TxId tx = new TxId("tx-j");

        // checkout(Logger, TxId, Payment, String)
        System.out.println(ContextParamsDemoKt.checkout(console, tx, new Payment(5_000), "coffee-shop"));
        // authorize(Logger, TxId, Payment receiver, String merchant)
        System.out.println(ContextParamsDemoKt.authorize(console, tx, new Payment(250_000), "car-dealer"));
        // audit(Logger, String)
        ContextParamsDemoKt.audit(console, "called from Java");
    }
}
