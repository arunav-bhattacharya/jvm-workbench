package workbench.modernjava.l02;

/**
 * Everything the library lends. The library owns this list, and the loan rules must handle
 * every kind of item on it. The one exception is {@link PartnerItem}: items lent to us by
 * partner libraries, which those libraries describe in their own code, outside this file.
 *
 * <p>Right now anyone can implement any of these interfaces, so the compiler can't check that
 * a switch over an item is complete.
 *
 * <p>TODO 1: seal {@code LibraryItem} so its direct subtypes are exactly {@code Book},
 * {@code Disc}, {@code Magazine} and {@code PartnerItem}.
 * <br>TODO 2: seal {@code Disc} so its only subtypes are {@code Dvd} and {@code AudioCd}.
 * <br>TODO 3: leave {@code PartnerItem} open to partner code. Every subtype of a sealed type
 * needs one of {@code final}, {@code sealed} or {@code non-sealed}: which one fits here?
 * The records need nothing: a record is already final.
 */
public interface LibraryItem {

    record Book(String isbn, String title) implements LibraryItem {}

    interface Disc extends LibraryItem {}

    record Dvd(String title, int minutes) implements Disc {}

    record AudioCd(String title, int tracks) implements Disc {}

    record Magazine(String title, int issue) implements LibraryItem {}

    /** Lent to us by a partner library, which writes its own class for it. */
    interface PartnerItem extends LibraryItem {
        String partnerId();

        int loanDays();
    }
}
