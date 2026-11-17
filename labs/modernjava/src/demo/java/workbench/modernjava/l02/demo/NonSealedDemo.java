package workbench.modernjava.l02.demo;

/** Each branch of a sealed hierarchy ends as final, sealed or non-sealed. */
public class NonSealedDemo {

    sealed interface LibraryItem permits Book, Disc, PartnerItem {}

    record Book(String title) implements LibraryItem {}                      // final: a leaf

    sealed interface Disc extends LibraryItem permits Dvd, AudioCd {}       // sealed: closed below

    record Dvd(String title) implements Disc {}

    record AudioCd(String title) implements Disc {}

    non-sealed interface PartnerItem extends LibraryItem {                  // non-sealed: open below
        String partnerId();
    }

    // a partner library's code: allowed, because PartnerItem is non-sealed
    record ArchiveBox(String partnerId, String contents) implements PartnerItem {}

    // Step 3: delete "abstract" here and compile.
    sealed abstract static class Extension permits FixedDays, SameAgain {}

    static final class FixedDays extends Extension {
        final int days;
        FixedDays(int days) { this.days = days; }
    }

    static final class SameAgain extends Extension {}

    static String describe(LibraryItem item) {
        return switch (item) {
            case Book b -> "book " + b.title();
            case Disc d -> "disc " + d;                          // one case for the sealed branch
            case PartnerItem p -> "partner " + p.partnerId();    // one case for the open branch
        };
    }

    // how many days a renewal adds to a loan
    static int extraDays(Extension e, int loanDays) {
        return switch (e) {
            case FixedDays f -> f.days;
            case SameAgain s -> loanDays;
        };
    }

    public static void main(String[] args) {
        System.out.println(describe(new Book("Dune")));
        System.out.println(describe(new Dvd("Paddington")));
        System.out.println(describe(new ArchiveBox("city-archive", "old maps")));
        System.out.println("PartnerItem.isSealed(): " + PartnerItem.class.isSealed());
        System.out.println("renewal: " + extraDays(new FixedDays(7), 21) + " and " + extraDays(new SameAgain(), 21) + " extra days");
    }
}
