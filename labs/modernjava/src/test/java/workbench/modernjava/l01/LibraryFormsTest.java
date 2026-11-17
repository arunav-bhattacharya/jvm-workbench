package workbench.modernjava.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LibraryFormsTest {

    private static final LocalDate MAY_2 = LocalDate.of(2026, 5, 2);
    private static final LocalDate MAY_23 = LocalDate.of(2026, 5, 23);

    // ---- Shelfmark ----

    @Test
    @DisplayName("Shelfmark trims and upper-cases the section, so \" fic \" and \"FIC\" are the same shelfmark")
    void shelfmarkNormalizesSection() {
        Shelfmark s = new Shelfmark(" fic ", 12);
        assertThat(s.section()).isEqualTo("FIC");
        assertThat(s).isEqualTo(new Shelfmark("FIC", 12));
        assertThat(s.hashCode()).isEqualTo(new Shelfmark("FIC", 12).hashCode());
    }

    @Test
    @DisplayName("Shelfmark rejects a section that isn't three letters, a shelf outside 1 to 999, and a null section")
    void shelfmarkRejectsBadInput() {
        assertThatThrownBy(() -> new Shelfmark("FICT", 1)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Shelfmark("F1C", 1)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Shelfmark("FIC", 0)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Shelfmark("FIC", 1_000)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new Shelfmark(null, 1))
                .isInstanceOf(NullPointerException.class)
                .hasMessageContaining("section");
    }

    @Test
    @DisplayName("next() moves one shelf along, and the last shelf has no next")
    void shelfmarkNext() {
        Shelfmark s = new Shelfmark("fic", 12);
        assertThat(s.next()).isEqualTo(new Shelfmark("FIC", 13));
        assertThat(s).as("the old shelfmark is unchanged").isEqualTo(new Shelfmark("FIC", 12));
        assertThatThrownBy(() -> new Shelfmark("FIC", 999).next()).isInstanceOf(IllegalArgumentException.class);
    }

    // ---- LoanSlip ----

    @Test
    @DisplayName("LoanSlip keeps its own copy of the titles: the caller's later changes don't leak in")
    void loanSlipCopiesTitles() {
        List<String> titles = new ArrayList<>(List.of("Dune"));
        LoanSlip slip = new LoanSlip("M-1042", MAY_2, titles);
        Set<LoanSlip> seen = new HashSet<>(Set.of(slip));

        titles.add("Emma");

        assertThat(slip.titles()).containsExactly("Dune");
        assertThat(seen).as("a slip used as a set key must stay findable").contains(slip);
        assertThatThrownBy(() -> slip.titles().add("x")).isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    @DisplayName("LoanSlip rejects a blank member id, no titles, and null parts")
    void loanSlipRejectsBadInput() {
        assertThatThrownBy(() -> new LoanSlip("  ", MAY_2, List.of("Dune"))).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new LoanSlip("M-1042", MAY_2, List.of())).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new LoanSlip("M-1042", null, List.of("Dune"))).isInstanceOf(NullPointerException.class);
        assertThatThrownBy(() -> new LoanSlip(null, MAY_2, List.of("Dune"))).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("withDue returns a new slip, leaves the old one alone, and checks the new date")
    void loanSlipWither() {
        LoanSlip slip = new LoanSlip("M-1042", MAY_2, List.of("Dune"));
        LoanSlip renewed = slip.withDue(MAY_23);

        assertThat(renewed).isEqualTo(new LoanSlip("M-1042", MAY_23, List.of("Dune")));
        assertThat(slip.due()).isEqualTo(MAY_2);
        assertThatThrownBy(() -> slip.withDue(null)).isInstanceOf(NullPointerException.class);
    }

    // ---- PhoneNumber ----

    @Test
    @DisplayName("PhoneNumber strips spaces and accepts only 7 to 15 digits")
    void phoneNumberValidates() {
        assertThat(new PhoneNumber("0161 496 0123").digits()).isEqualTo("01614960123");
        assertThatThrownBy(() -> new PhoneNumber("12345")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new PhoneNumber("0161-496-0123")).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new PhoneNumber(null)).isInstanceOf(NullPointerException.class);
    }

    @Test
    @DisplayName("PhoneNumber.toString shows only the last four digits, and equality still uses the real number")
    void phoneNumberMasksToString() {
        PhoneNumber p = new PhoneNumber("01614960123");
        assertThat(p.toString()).isEqualTo("PhoneNumber[****0123]");
        assertThat(p.last4()).isEqualTo("0123");
        assertThat(p.digits()).as("the accessor is not masked").isEqualTo("01614960123");
        // the record contract: a copy built from the accessors equals the original
        assertThat(new PhoneNumber(p.digits())).isEqualTo(p);
        assertThat(new PhoneNumber("01614960999")).isNotEqualTo(p);
    }
}
