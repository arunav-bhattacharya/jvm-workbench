package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public record ChargeTemplate(String merchantId, long amountMinor, List<String> tags, Map<String, String> metadata) {

    // compact canonical constructor: every path that makes a template goes through here,
    // the withers included, so every template owns unmodifiable copies
    public ChargeTemplate {
        tags = List.copyOf(tags);
        metadata = Map.copyOf(metadata);
    }

    public ChargeTemplate forMerchant(String otherMerchantId) {
        // sharing is now safe: the collections can't change
        return new ChargeTemplate(otherMerchantId, amountMinor, tags, metadata);
    }

    public ChargeTemplate withTag(String tag) {
        List<String> copy = new ArrayList<>(tags);      // copy, change the copy, wrap it again
        copy.add(tag);
        return new ChargeTemplate(merchantId, amountMinor, copy, metadata);
    }

    public ChargeTemplate withMetadata(String key, String value) {
        Map<String, String> copy = new HashMap<>(metadata);
        copy.put(key, value);
        return new ChargeTemplate(merchantId, amountMinor, tags, copy);
    }
}
