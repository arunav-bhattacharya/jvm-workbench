package workbench.modernjava.l02;

import workbench.modernjava.l02.LibraryItem.AudioCd;
import workbench.modernjava.l02.LibraryItem.Book;
import workbench.modernjava.l02.LibraryItem.Disc;
import workbench.modernjava.l02.LibraryItem.Dvd;
import workbench.modernjava.l02.LibraryItem.Magazine;
import workbench.modernjava.l02.LibraryItem.PartnerItem;

/** The library's loan rules, one exhaustive switch per rule. No {@code default} anywhere. */
public final class Loans {
    private Loans() {}

    /**
     * TODO 4: how many days a member may keep the item.
     * Book 21, Dvd 7, AudioCd 14, Magazine 0 (magazines stay in the reading room), and a
     * PartnerItem says for itself ({@code loanDays()}).
     * Write a switch with one case per type and no {@code default}. Once the hierarchy is sealed,
     * javac accepts it; before that, it can't.
     */
    public static int loanDays(LibraryItem item) {
        throw new UnsupportedOperationException("TODO: loanDays");
    }

    /**
     * TODO 5: which bin a returned item goes into at the returns desk: {@code "books"},
     * {@code "discs"} for both kinds of disc, {@code "magazines"}, and
     * {@code "partner:" + partnerId()} for a partner's item.
     * Use one case for all discs: {@code Disc} is sealed, so one case covers it.
     */
    public static String returnBin(LibraryItem item) {
        throw new UnsupportedOperationException("TODO: returnBin");
    }
}
