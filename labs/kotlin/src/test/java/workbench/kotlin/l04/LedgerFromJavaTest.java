package workbench.kotlin.l04;

import kotlin.Unit;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class LedgerFromJavaTest {

    @Test
    @DisplayName("Java calls the DSL with a Function1<EntryBuilder, Unit>: the receiver is the first parameter")
    void javaPassesTheBuilderAsAParameter() {
        JournalEntry e = LedgerKt.journalEntry("payout-981", b -> {
            b.setMemo("merchant payout");
            b.debit("merchant:981", 12_000L);
            b.credit("bank:clearing", 12_000L);
            return Unit.INSTANCE;                      // a Kotlin () -> Unit returns Unit, so Java must too
        });
        assertThat(e.getPostings()).hasSize(2);
        assertThat(e.getMemo()).isEqualTo("merchant payout");
    }
}
