package workbench.modernjava.l01;

import java.util.Objects;

public record CardNumber(String digits) {

    public CardNumber {
        Objects.requireNonNull(digits, "digits");
        digits = digits.replace(" ", "");
        if (!digits.matches("[0-9]{12,19}")) {
            throw new IllegalArgumentException("a card number has 12 to 19 digits");
        }
    }

    public String last4() {
        return digits.substring(digits.length() - 4);
    }

    // mask toString, not the accessor: the generated toString reads the field directly,
    // so overriding digits() would not hide anything from the logs
    @Override
    public String toString() {
        return "CardNumber[****" + last4() + "]";
    }
}
