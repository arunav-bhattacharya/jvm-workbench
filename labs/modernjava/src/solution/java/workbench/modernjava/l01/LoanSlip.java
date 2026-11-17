package workbench.modernjava.l01;

import java.time.LocalDate;
import java.util.List;
import java.util.Objects;

public record LoanSlip(String memberId, LocalDate due, List<String> titles) {

    public LoanSlip {
        Objects.requireNonNull(memberId, "memberId");
        Objects.requireNonNull(due, "due");
        if (memberId.isBlank()) {
            throw new IllegalArgumentException("blank memberId");
        }
        // a record is only as immutable as its components: copy the caller's list.
        // List.copyOf also throws NullPointerException for a null list or a null element.
        titles = List.copyOf(titles);
        if (titles.isEmpty()) {
            throw new IllegalArgumentException("a loan slip needs at least one title");
        }
    }

    // a hand-written wither: it calls the canonical constructor, so the new value is checked too
    public LoanSlip withDue(LocalDate newDue) {
        return new LoanSlip(memberId, newDue, titles);
    }
}
