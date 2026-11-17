// Java equivalent of TransparencyTrap.kt: a hand-written push "flow" has no inspector, so the
// try/catch around the call swallows the diner's complaint and carries on with the next dish.
package workbench.flows.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

public class TransparencyTrapJava {
    static class SentBackException extends RuntimeException {
        SentBackException(String message) { super(message); }
    }

    static final List<String> DINNER = List.of("soup", "salad", "roast");

    static void plates(Consumer<String> diner) {
        for (String dish : DINNER) {
            try {
                diner.accept(dish);
            } catch (RuntimeException e) {
                System.out.println("SORRY " + dish + " came back, serving the next dish. " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        List<String> eaten = new ArrayList<>();
        plates(dish -> {
            if (dish.equals("salad")) throw new SentBackException("too salty: " + dish);
            eaten.add(dish);
        });
        System.out.println("plates returned normally. eaten=" + eaten);
    }
}
