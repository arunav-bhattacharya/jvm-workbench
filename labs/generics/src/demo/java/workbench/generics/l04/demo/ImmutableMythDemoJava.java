package workbench.generics.l04.demo;

import java.util.ArrayList;
import java.util.List;

/** Java twin of ImmutableMythDemo.kt. A ? extends view stops adds, not changes. */
public class ImmutableMythDemoJava {
    public static void main(String[] args) {
        List<CardPayment> cards = new ArrayList<>(List.of(new CardPayment("pay_1", 1_200, "4242"), new CardPayment("pay_2", 350, "0005")));
        List<? extends Payment> view = cards;           // read-only for the TYPE, not for the state

        Payment taken = view.remove(0);                 // compiles: remove hands a value out
        System.out.println("took " + taken.getId() + ", " + view.size() + " left");
        view.clear();                                   // compiles: no T involved
        System.out.println("after clear: " + view.size() + " left, and cards has " + cards.size());

        // view.add(new CardPayment("pay_4", 10, "2222"));   // uncomment: which rule stops this?
    }
}
