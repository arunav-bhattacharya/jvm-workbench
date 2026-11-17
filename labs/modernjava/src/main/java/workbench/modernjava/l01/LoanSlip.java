package workbench.modernjava.l01;

import java.time.LocalDate;
import java.util.List;

/**
 * The slip a member takes home: who borrowed, when the books are due back, and which titles.
 *
 * <p>TODO 3: add a compact canonical constructor that
 * <ul>
 *   <li>rejects a null {@code memberId}, {@code due} or {@code titles} with a {@link NullPointerException},</li>
 *   <li>rejects a blank {@code memberId} with an {@link IllegalArgumentException},</li>
 *   <li>replaces {@code titles} with an unmodifiable copy, so later changes to the caller's
 *       list don't show up in the record,</li>
 *   <li>rejects an empty list of titles with an {@link IllegalArgumentException}.</li>
 * </ul>
 */
public record LoanSlip(String memberId, LocalDate due, List<String> titles) {

    /**
     * TODO 4: a renewal. Returns a slip like this one but due back on {@code newDue}.
     * The new slip must pass the same checks as any other slip.
     */
    public LoanSlip withDue(LocalDate newDue) {
        throw new UnsupportedOperationException("TODO: withDue");
    }
}
