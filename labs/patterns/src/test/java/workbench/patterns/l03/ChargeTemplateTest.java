package workbench.patterns.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ChargeTemplateTest {

    private static ChargeTemplate original() {
        // mutable inputs on purpose: that is what callers really pass
        return new ChargeTemplate("ops", 4_900, new ArrayList<>(List.of("monthly")), new HashMap<>(Map.of("plan", "pro")));
    }

    @Test
    @DisplayName("Tagging a merchant's copy leaves the original and other copies alone")
    void withTagDoesNotLeak() {
        ChargeTemplate base = original();
        ChargeTemplate acme = base.forMerchant("m-acme");
        ChargeTemplate globex = base.forMerchant("m-globex");

        ChargeTemplate acmeTagged = acme.withTag("vip");

        assertThat(acmeTagged.tags()).containsExactly("monthly", "vip");
        assertThat(acme.tags()).as("the copy that was tagged").containsExactly("monthly");
        assertThat(base.tags()).as("the original").containsExactly("monthly");
        assertThat(globex.tags()).as("another merchant's copy").containsExactly("monthly");
    }

    @Test
    @DisplayName("withMetadata returns a changed copy and leaves the original alone")
    void withMetadataDoesNotLeak() {
        ChargeTemplate base = original();
        ChargeTemplate changed = base.withMetadata("plan", "enterprise").withMetadata("region", "eu");

        assertThat(changed.metadata()).containsEntry("plan", "enterprise").containsEntry("region", "eu");
        assertThat(base.metadata()).containsExactlyEntriesOf(Map.of("plan", "pro"));
    }

    @Test
    @DisplayName("Changing the list you passed in does not change the template")
    void defensiveCopyOnConstruction() {
        List<String> tags = new ArrayList<>(List.of("monthly"));
        Map<String, String> meta = new HashMap<>(Map.of("plan", "pro"));
        ChargeTemplate t = new ChargeTemplate("m-1", 100, tags, meta);

        tags.add("sneaky");
        meta.put("plan", "free");

        assertThat(t.tags()).containsExactly("monthly");
        assertThat(t.metadata()).containsEntry("plan", "pro");
    }

    @Test
    @DisplayName("The collections a template hands out can't be modified")
    void accessorsAreUnmodifiable() {
        ChargeTemplate t = original();
        assertThatThrownBy(() -> t.tags().add("x")).isInstanceOf(UnsupportedOperationException.class);
        assertThatThrownBy(() -> t.metadata().put("x", "y")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    @DisplayName("forMerchant keeps the amount, tags and metadata and changes only the merchant")
    void forMerchantCopiesValues() {
        ChargeTemplate copy = original().forMerchant("m-acme");
        assertThat(copy.merchantId()).isEqualTo("m-acme");
        assertThat(copy.amountMinor()).isEqualTo(4_900);
        assertThat(copy.tags()).containsExactly("monthly");
        assertThat(copy.metadata()).containsExactlyEntriesOf(Map.of("plan", "pro"));
        assertThat(copy).isEqualTo(new ChargeTemplate("m-acme", 4_900, List.of("monthly"), Map.of("plan", "pro")));
    }
}
