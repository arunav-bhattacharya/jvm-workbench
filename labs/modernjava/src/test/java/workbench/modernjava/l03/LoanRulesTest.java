package workbench.modernjava.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import workbench.modernjava.l03.LoanRules.Book;
import workbench.modernjava.l03.LoanRules.Branch;
import workbench.modernjava.l03.LoanRules.Disc;
import workbench.modernjava.l03.LoanRules.Format;
import workbench.modernjava.l03.LoanRules.Item;
import workbench.modernjava.l03.LoanRules.Loan;
import workbench.modernjava.l03.LoanRules.Magazine;
import workbench.modernjava.l03.LoanRules.Member;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LoanRulesTest {

    private static final Member ADULT = new Member("M-1042", 34);
    private static final Member CHILD = new Member("M-3001", 8);

    private static Loan loan(Member member, Item item, Branch branch) {
        return new Loan(member, item, branch);
    }

    private static Book book(Format f) { return new Book(f, false); }

    private static Book newRelease(Format f) { return new Book(f, true); }

    @Test
    @DisplayName("book loans: large print 42 days, new releases 7, from the library bus 28, any other book 21")
    void bookLoans() {
        assertThat(LoanRules.loanDays(loan(ADULT, book(Format.LARGE_PRINT), Branch.CENTRAL))).isEqualTo(42);
        assertThat(LoanRules.loanDays(loan(ADULT, newRelease(Format.HARDBACK), Branch.CENTRAL))).isEqualTo(7);
        assertThat(LoanRules.loanDays(loan(ADULT, book(Format.PAPERBACK), Branch.BUS))).isEqualTo(28);
        assertThat(LoanRules.loanDays(loan(ADULT, book(Format.PAPERBACK), Branch.CENTRAL))).isEqualTo(21);
        assertThat(LoanRules.loanDays(loan(ADULT, book(Format.HARDBACK), Branch.NORTH))).isEqualTo(21);
    }

    @Test
    @DisplayName("rule order matters: a new large-print book gets 42 days, a new release from the bus gets 7")
    void ruleOrder() {
        assertThat(LoanRules.loanDays(loan(ADULT, newRelease(Format.LARGE_PRINT), Branch.CENTRAL))).isEqualTo(42);
        assertThat(LoanRules.loanDays(loan(ADULT, newRelease(Format.PAPERBACK), Branch.BUS))).isEqualTo(7);
    }

    @Test
    @DisplayName("discs: 14 days for a box set, 7 otherwise, from any branch")
    void discLoans() {
        assertThat(LoanRules.loanDays(loan(ADULT, new Disc(true), Branch.NORTH))).isEqualTo(14);
        assertThat(LoanRules.loanDays(loan(ADULT, new Disc(false), Branch.NORTH))).isEqualTo(7);
        assertThat(LoanRules.loanDays(loan(ADULT, new Disc(false), Branch.BUS))).isEqualTo(7);
    }

    @Test
    @DisplayName("magazines: 14 days for a child under 12, 7 for everyone else")
    void magazineLoans() {
        assertThat(LoanRules.loanDays(loan(CHILD, new Magazine("Kite Club"), Branch.CENTRAL))).isEqualTo(14);
        assertThat(LoanRules.loanDays(loan(new Member("M-3002", 11), new Magazine("Kite Club"), Branch.BUS))).isEqualTo(14);
        assertThat(LoanRules.loanDays(loan(new Member("M-3003", 12), new Magazine("Kite Club"), Branch.BUS))).isEqualTo(7);
        assertThat(LoanRules.loanDays(loan(ADULT, new Magazine("Garden Monthly"), Branch.CENTRAL))).isEqualTo(7);
    }

    @Test
    @DisplayName("a member's age only matters for magazines")
    void ageOnlyForMagazines() {
        assertThat(LoanRules.loanDays(loan(CHILD, book(Format.PAPERBACK), Branch.CENTRAL))).isEqualTo(21);
        assertThat(LoanRules.loanDays(loan(CHILD, new Disc(false), Branch.CENTRAL))).isEqualTo(7);
    }

    @Test
    @DisplayName("loanDays(null) throws NullPointerException")
    void loanDaysOfNull() {
        assertThatThrownBy(() -> LoanRules.loanDays(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("label names each item, with large print first and new releases marked")
    void labels() {
        assertThat(LoanRules.label(newRelease(Format.LARGE_PRINT))).isEqualTo("LARGE_PRINT");
        assertThat(LoanRules.label(book(Format.LARGE_PRINT))).isEqualTo("LARGE_PRINT");
        assertThat(LoanRules.label(newRelease(Format.HARDBACK))).isEqualTo("HARDBACK new");
        assertThat(LoanRules.label(book(Format.PAPERBACK))).isEqualTo("PAPERBACK");
        assertThat(LoanRules.label(new Disc(true))).isEqualTo("box set");
        assertThat(LoanRules.label(new Disc(false))).isEqualTo("disc");
        assertThat(LoanRules.label(new Magazine("Garden Monthly"))).isEqualTo("magazine Garden Monthly");
    }

    @Test
    @DisplayName("label handles a null item and a magazine whose title is null")
    void labelNulls() {
        assertThat(LoanRules.label(null)).isEqualTo("no item");
        assertThat(LoanRules.label(new Magazine(null))).isEqualTo("magazine ?");
    }
}
