package workbench.kotlin.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class JobFromJavaTest {

    @Test
    @DisplayName("Java sees plain getters and setters: the delegate is invisible, but it still records")
    void javaUsesPlainAccessors() {
        PrintJob job = new PrintJob(new ChangeLog());
        job.setStatus("QUEUED");                // compiles to status$delegate.setValue(this, KProperty, value)
        job.setCopies(250);
        assertThat(job.getStatus()).isEqualTo("QUEUED");
        assertThat(job.getLog().getChanges()).containsExactly(
                new Change("status", "NEW", "QUEUED"),
                new Change("copies", 1, 250));
    }
}
