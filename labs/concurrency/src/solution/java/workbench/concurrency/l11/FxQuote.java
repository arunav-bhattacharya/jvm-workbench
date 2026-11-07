package workbench.concurrency.l11;

import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;

public record FxQuote(String pair, List<Tier> tiers, byte[] signature) {

    public FxQuote {
        Objects.requireNonNull(pair, "pair");
        tiers = List.copyOf(tiers);          // 1. an unmodifiable COPY: the caller's list can change, ours can't
        signature = signature.clone();       // 2. arrays are always mutable: copy on the way in
    }

    @Override
    public byte[] signature() {
        return signature.clone();            // 3. ...and on the way out
    }

    public record Tier(long upToCents, BigDecimal rate) {}   // long and BigDecimal are immutable already
}
