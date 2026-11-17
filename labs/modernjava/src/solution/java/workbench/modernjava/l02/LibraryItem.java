package workbench.modernjava.l02;

// sealed: only these four may implement LibraryItem directly. With every subtype in this
// file, the permits clause could be left out and javac would infer the same list.
public sealed interface LibraryItem
        permits LibraryItem.Book, LibraryItem.Disc, LibraryItem.Magazine, LibraryItem.PartnerItem {

    record Book(String isbn, String title) implements LibraryItem {}            // records are final

    // a sealed branch: closed to new kinds of disc
    sealed interface Disc extends LibraryItem permits Dvd, AudioCd {}

    record Dvd(String title, int minutes) implements Disc {}

    record AudioCd(String title, int tracks) implements Disc {}

    record Magazine(String title, int issue) implements LibraryItem {}

    // non-sealed: deliberately reopens this branch, so partner libraries may implement it
    non-sealed interface PartnerItem extends LibraryItem {
        String partnerId();

        int loanDays();
    }
}
