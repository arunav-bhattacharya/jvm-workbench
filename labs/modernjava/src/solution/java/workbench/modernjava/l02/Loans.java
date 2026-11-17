package workbench.modernjava.l02;

import workbench.modernjava.l02.LibraryItem.AudioCd;
import workbench.modernjava.l02.LibraryItem.Book;
import workbench.modernjava.l02.LibraryItem.Disc;
import workbench.modernjava.l02.LibraryItem.Dvd;
import workbench.modernjava.l02.LibraryItem.Magazine;
import workbench.modernjava.l02.LibraryItem.PartnerItem;

public final class Loans {
    private Loans() {}

    public static int loanDays(LibraryItem item) {
        return switch (item) {                     // no default: a new kind of item breaks the build here
            case Book b -> 21;
            case Dvd d -> 7;
            case AudioCd cd -> 14;
            case Magazine m -> 0;
            case PartnerItem p -> p.loanDays();    // covers every partner class, known or not
        };
    }

    public static String returnBin(LibraryItem item) {
        return switch (item) {
            case Book b -> "books";
            case Disc d -> "discs";                // Disc is sealed, so this one case covers Dvd and AudioCd
            case Magazine m -> "magazines";
            case PartnerItem p -> "partner:" + p.partnerId();
        };
    }
}
