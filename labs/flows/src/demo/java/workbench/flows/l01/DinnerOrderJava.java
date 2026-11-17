// Java equivalent of DinnerOrder.kt. Java has no Flow, so this is a hand-written push "flow":
// the cook calls the diner's Consumer once per dish, on the same thread.
package workbench.flows.l01;

import java.util.List;
import java.util.function.Consumer;

public class DinnerOrderJava {
    static void cookDinner(List<String> card, Consumer<String> diner) {
        for (String dish : card) {
            System.out.println("cook    " + dish);
            diner.accept(dish);
            System.out.println("accept(" + dish + ") returned");
        }
    }

    public static void main(String[] args) {
        List<String> card = List.of("soup", "salad", "roast");
        System.out.println("cook ready");

        cookDinner(card, dish -> System.out.println("eat     " + dish));
        System.out.println("cookDinner returned");
    }
}
