package workbench.modernjava.l01;

import java.util.Objects;

public record PhoneNumber(String digits) {

    public PhoneNumber {
        Objects.requireNonNull(digits, "digits");
        digits = digits.replace(" ", "");
        if (!digits.matches("[0-9]{7,15}")) {
            throw new IllegalArgumentException("a phone number has 7 to 15 digits");
        }
    }

    public String last4() {
        return digits.substring(digits.length() - 4);
    }

    // mask toString, not the accessor: the generated toString reads the field directly,
    // so overriding digits() would not hide anything from the logs
    @Override
    public String toString() {
        return "PhoneNumber[****" + last4() + "]";
    }
}
