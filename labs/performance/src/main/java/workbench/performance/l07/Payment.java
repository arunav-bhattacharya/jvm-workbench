package workbench.performance.l07;

/** One payment as it arrives from the API: the amount is a decimal string such as "1234.56". */
public record Payment(String id, String currency, String amount, String merchant) { }
