package workbench.executors.l06;

import java.math.BigDecimal;

/** The FX provider. Blocking: returns how many units of {@code to} one unit of {@code from} buys. */
public interface FxService {
    BigDecimal rate(String from, String to);
}
