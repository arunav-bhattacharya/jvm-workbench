package workbench.kotlin.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class DraftFromJavaTest {

    @Test
    @DisplayName("Java sees plain getters and setters: the delegate is invisible, but it still records")
    void javaUsesPlainAccessors() {
        PaymentDraft draft = new PaymentDraft(new ChangeLog());
        draft.setStatus("AUTHORIZED");          // compiles to status$delegate.setValue(this, KProperty, value)
        draft.setAmountMinor(2_500L);
        assertThat(draft.getStatus()).isEqualTo("AUTHORIZED");
        assertThat(draft.getLog().getChanges()).containsExactly(
                new Change("status", "NEW", "AUTHORIZED"),
                new Change("amountMinor", 0L, 2_500L));
    }
}
