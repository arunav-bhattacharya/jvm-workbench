package workbench.generics.l04.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Java twin of ListOutDemo.kt. Java writes the read-only view as List<? extends Payment> at each use.
 * It also calls the Kotlin function sumCents: Kotlin compiled its List<Payment> parameter as
 * List<? extends Payment>, because Kotlin's List is declared `out`.
 */
public class ListOutDemoJava {

    static long sumCentsJava(List<? extends Payment> payments) {
        long sum = 0;
        for (Payment p : payments) sum += p.getCents();
        return sum;
    }

    static long sumCentsInvariant(List<Payment> payments) {
        return sumCentsJava(payments);
    }

    public static void main(String[] args) {
        List<CardPayment> cards = new ArrayList<>(List.of(new CardPayment("pay_1", 1_200, "4242"), new CardPayment("pay_2", 350, "0005")));
        System.out.println("sumCentsJava(cards) = " + sumCentsJava(cards));
        System.out.println("Kotlin's sumCents(cards) from Java = " + ListOutDemoKt.sumCents(cards));

        // Wrong moves. Uncomment ONE at a time, predict the error, then run.
        // System.out.println(sumCentsInvariant(cards));
        // System.out.println(ListOutDemoKt.sumCentsMutable(cards));
    }
}
