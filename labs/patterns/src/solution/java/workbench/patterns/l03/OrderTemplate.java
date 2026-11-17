package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public record OrderTemplate(String customer, long priceCents, List<String> tags, Map<String, String> notes) {

    // compact canonical constructor: every path that makes a template goes through here,
    // the withers included, so every template owns unmodifiable copies
    public OrderTemplate {
        tags = List.copyOf(tags);
        notes = Map.copyOf(notes);
    }

    public OrderTemplate forCustomer(String otherCustomer) {
        // sharing is now safe: the collections can't change
        return new OrderTemplate(otherCustomer, priceCents, tags, notes);
    }

    public OrderTemplate withTag(String tag) {
        List<String> copy = new ArrayList<>(tags);      // copy, change the copy, wrap it again
        copy.add(tag);
        return new OrderTemplate(customer, priceCents, copy, notes);
    }

    public OrderTemplate withNote(String key, String value) {
        Map<String, String> copy = new HashMap<>(notes);
        copy.put(key, value);
        return new OrderTemplate(customer, priceCents, tags, copy);
    }
}
