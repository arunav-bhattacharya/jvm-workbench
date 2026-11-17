package workbench.patterns.l03;

import java.util.List;
import java.util.Map;

/**
 * A prototype for regular orders, such as the Saturday breakfast box: the shop sets up one template,
 * and each customer gets a copy with their own name, tags and notes.
 *
 * <p>The copies are shallow. {@link #forCustomer} shares the tag list and the notes map with the
 * original, and {@link #withTag} adds to that shared list, so tagging one customer's copy tags every
 * template made from the same original. The record also keeps whatever list the caller passed in,
 * so the caller can change a template after building it.
 *
 * <p>Fix it so every template owns unmodifiable copies of its collections, and the withers return new
 * templates without touching the original. Keep the public signatures.
 */
public record OrderTemplate(String customer, long priceCents, List<String> tags, Map<String, String> notes) {

    /** A copy of this template for another customer. */
    public OrderTemplate forCustomer(String otherCustomer) {
        return new OrderTemplate(otherCustomer, priceCents, tags, notes);
    }

    /** A copy with one more tag at the end. */
    public OrderTemplate withTag(String tag) {
        tags.add(tag);                       // changes the list the original shares
        return new OrderTemplate(customer, priceCents, tags, notes);
    }

    /** A copy with one note added or replaced. */
    public OrderTemplate withNote(String key, String value) {
        notes.put(key, value);               // same problem
        return new OrderTemplate(customer, priceCents, tags, notes);
    }
}
