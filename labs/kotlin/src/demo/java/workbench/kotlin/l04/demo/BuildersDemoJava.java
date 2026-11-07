package workbench.kotlin.l04.demo;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Java twin of BuildersDemo.kt. Java builds a mutable collection, then copies it into an
 * unmodifiable one. buildList and buildString are inline-only Kotlin functions, so Java can't call them.
 */
public class BuildersDemoJava {

    record ItemJava(String sku, int qty, long unitMinor) {}

    public static void main(String[] args) {
        List<ItemJava> building = new ArrayList<>();
        building.add(new ItemJava("sku-1", 2, 999));
        building.add(new ItemJava("sku-2", 1, 500));
        if (building.size() == 2) building.add(new ItemJava("gift-wrap", 1, 0));
        List<ItemJava> items = List.copyOf(building);

        Map<String, Long> totals = new LinkedHashMap<>();
        for (ItemJava i : items) totals.put(i.sku(), i.qty() * i.unitMinor());

        String text = new StringBuilder()
                .append("total=")
                .append(totals.values().stream().mapToLong(Long::longValue).sum())
                .toString();

        System.out.println(items.stream().map(ItemJava::sku).toList());
        System.out.println(totals);
        System.out.println(text);
        try {
            items.add(new ItemJava("late", 1, 1));
        } catch (UnsupportedOperationException e) {
            System.out.println("the copied list is read-only: " + e.getClass().getSimpleName());
        }
    }
}
