package workbench.kotlin.l04.demo;

import kotlin.Unit;

/**
 * Java twin of DslMarkerDemo.kt. Java calls the same Kotlin DSL with Function1 lambdas. It needs no
 * marker: each block names its builder, so reaching the outer one means typing `r.` on purpose.
 */
public class DslMarkerDemoJava {
    public static void main(String[] args) {
        PaymentRequest req = DslMarkerDemoKt.paymentRequest("PR-1", r -> {
            r.setCurrency("GBP");
            r.payer(p -> {
                p.setName("ACME Ltd");
                p.setIban("GB33BUKB20201555555555");
                return Unit.INSTANCE;
            });
            r.payee(p -> {
                p.setName("Corner Shop");
                p.setIban("GB94BARC10201530093459");
                r.setCurrency("EUR");                 // the outer builder, named explicitly
                return Unit.INSTANCE;
            });
            return Unit.INSTANCE;
        });
        System.out.println(req);
    }
}
