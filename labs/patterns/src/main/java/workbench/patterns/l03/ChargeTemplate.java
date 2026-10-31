package workbench.patterns.l03;

import java.util.List;
import java.util.Map;

/**
 * A prototype for recurring charges: the operations team sets one up, and each merchant gets a
 * copy with its own id, tags and metadata.
 *
 * <p>The copies are shallow. {@link #forMerchant} shares the tag list and the metadata map with the
 * original, and {@link #withTag} adds to that shared list, so tagging one merchant's copy tags every
 * template made from the same original. The record also keeps whatever list the caller passed in,
 * so the caller can change a template after building it.
 *
 * <p>Fix it so every template owns immutable copies of its collections, and the withers return new
 * templates without touching the original. Keep the public signatures.
 */
public record ChargeTemplate(String merchantId, long amountMinor, List<String> tags, Map<String, String> metadata) {

    /** A copy of this template for another merchant. */
    public ChargeTemplate forMerchant(String otherMerchantId) {
        return new ChargeTemplate(otherMerchantId, amountMinor, tags, metadata);
    }

    /** A copy with one more tag at the end. */
    public ChargeTemplate withTag(String tag) {
        tags.add(tag);                       // mutates the list the original shares
        return new ChargeTemplate(merchantId, amountMinor, tags, metadata);
    }

    /** A copy with one metadata entry added or replaced. */
    public ChargeTemplate withMetadata(String key, String value) {
        metadata.put(key, value);            // same problem
        return new ChargeTemplate(merchantId, amountMinor, tags, metadata);
    }
}
