package workbench.patterns.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class OrderTemplateTest {

    private static OrderTemplate original() {
        // mutable inputs on purpose: that is what callers really pass
        return new OrderTemplate("shop", 1_490, new ArrayList<>(List.of("weekly")), new HashMap<>(Map.of("box", "breakfast")));
    }

    @Test
    @DisplayName("Tagging one customer's copy leaves the original and other copies alone")
    void withTagDoesNotLeak() {
        OrderTemplate base = original();
        OrderTemplate anna = base.forCustomer("anna");
        OrderTemplate ben = base.forCustomer("ben");

        OrderTemplate annaTagged = anna.withTag("no nuts");

        assertThat(annaTagged.tags()).containsExactly("weekly", "no nuts");
        assertThat(anna.tags()).as("the copy that was tagged").containsExactly("weekly");
        assertThat(base.tags()).as("the original").containsExactly("weekly");
        assertThat(ben.tags()).as("another customer's copy").containsExactly("weekly");
    }

    @Test
    @DisplayName("withNote returns a changed copy and leaves the original alone")
    void withNoteDoesNotLeak() {
        OrderTemplate base = original();
        OrderTemplate changed = base.withNote("box", "brunch").withNote("door", "side gate");

        assertThat(changed.notes()).containsEntry("box", "brunch").containsEntry("door", "side gate");
        assertThat(base.notes()).containsExactlyEntriesOf(Map.of("box", "breakfast"));
    }

    @Test
    @DisplayName("Changing the list you passed in does not change the template")
    void defensiveCopyOnConstruction() {
        List<String> tags = new ArrayList<>(List.of("weekly"));
        Map<String, String> notes = new HashMap<>(Map.of("box", "breakfast"));
        OrderTemplate t = new OrderTemplate("cleo", 100, tags, notes);

        tags.add("sneaky");
        notes.put("box", "empty");

        assertThat(t.tags()).containsExactly("weekly");
        assertThat(t.notes()).containsEntry("box", "breakfast");
    }

    @Test
    @DisplayName("The collections a template hands out can't be modified")
    void accessorsAreUnmodifiable() {
        OrderTemplate t = original();
        assertThatThrownBy(() -> t.tags().add("x")).isInstanceOf(UnsupportedOperationException.class);
        assertThatThrownBy(() -> t.notes().put("x", "y")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    @DisplayName("forCustomer keeps the price, tags and notes and changes only the customer")
    void forCustomerCopiesValues() {
        OrderTemplate copy = original().forCustomer("anna");
        assertThat(copy.customer()).isEqualTo("anna");
        assertThat(copy.priceCents()).isEqualTo(1_490);
        assertThat(copy.tags()).containsExactly("weekly");
        assertThat(copy.notes()).containsExactlyEntriesOf(Map.of("box", "breakfast"));
        assertThat(copy).isEqualTo(new OrderTemplate("anna", 1_490, List.of("weekly"), Map.of("box", "breakfast")));
    }
}
