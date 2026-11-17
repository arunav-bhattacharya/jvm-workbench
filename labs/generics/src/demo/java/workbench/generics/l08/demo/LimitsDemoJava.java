package workbench.generics.l08.demo;

import java.util.List;

/**
 * Java twin of LimitsDemo.kt. The closest Java equivalent passes a Class token, and a Class token
 * has the same limit as a reified T: List.class stands for every List, whatever its elements.
 */
public class LimitsDemoJava {

    @SuppressWarnings("unchecked")
    static <T> List<T> filterIsInstance(List<?> items, Class<?> type) {
        return (List<T>) items.stream().filter(type::isInstance).toList();
    }

    public static void main(String[] args) {
        List<Object> boxes = List.of(List.of(180, 150), List.of("Gala"), "Fuji");
        List<List<String>> nameLists = filterIsInstance(boxes, List.class);  // there is no List<String>.class
        System.out.println("lists of names? " + nameLists);

        // getClass() on a value: a null receiver is only found at run time.
        Object maybe = null;
        try {
            System.out.println(maybe.getClass());
        } catch (NullPointerException e) {
            System.out.println("NullPointerException from getClass() on null");
        }

        // Uncomment, predict, then run: it compiles, so what happens at run time?
        // String n = nameLists.get(0).get(0);
    }
}
