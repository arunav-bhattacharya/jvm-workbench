package workbench.kotlin.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ReviewFromJavaTest {

    @Test
    @DisplayName("Java passes the context parameters first, then the receiver, then the ordinary arguments")
    void javaSeesLeadingParameters() {
        List<String> lines = new ArrayList<>();
        Logbook logbook = lines::add;
        // Kotlin: context(logbook: Logbook, shift: Shift) fun JobRequest.review(maxCopies: Int)
        // JVM:    static Decision review(Logbook, Shift, JobRequest, int)
        Decision d = ReviewKt.review(logbook, new Shift("java"), new JobRequest(40, "a3", "poster.pdf"), 1_000);
        assertThat(d).isSameAs(Decision.Accepted.INSTANCE);
        assertThat(lines).containsExactly("[java] accepted 40 on A3");
    }
}
