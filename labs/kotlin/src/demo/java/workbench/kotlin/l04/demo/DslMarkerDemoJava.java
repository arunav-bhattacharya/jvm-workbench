package workbench.kotlin.l04.demo;

import kotlin.Unit;

/**
 * Java twin of DslMarkerDemo.kt. Java calls the same Kotlin DSL with Function1 lambdas. It needs no
 * marker: each block names its builder, so reaching the outer one means typing `f.` on purpose.
 */
public class DslMarkerDemoJava {
    public static void main(String[] args) {
        OrderForm form = DslMarkerDemoKt.orderForm("ord-17", f -> {
            f.setCopies(100);
            f.customer(c -> {
                c.setName("Corner Bakery");
                c.setPhone("555-0142");
                return Unit.INSTANCE;
            });
            f.deliverTo(c -> {
                c.setName("Corner Bakery, back door");
                c.setPhone("555-0143");
                f.setCopies(250);                     // the outer builder, named explicitly
                return Unit.INSTANCE;
            });
            return Unit.INSTANCE;
        });
        System.out.println(form);
    }
}
