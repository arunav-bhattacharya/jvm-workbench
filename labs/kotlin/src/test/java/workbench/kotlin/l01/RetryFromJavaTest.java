package workbench.kotlin.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class RetryFromJavaTest {

    @Test
    @DisplayName("Java calls retry as an ordinary static method on RetryKt: javac inlines nothing")
    void javaCallsTheCompiledBody() {
        AtomicInteger calls = new AtomicInteger();
        // Java sees: static <T> T retry(int, Function1<? super Exception, Boolean>, Function1<? super Integer, ? extends T>)
        String result = RetryKt.retry(3, e -> true, attempt -> {
            calls.incrementAndGet();
            if (attempt < 2) throw new IllegalStateException("issuer timeout");
            return "approved@" + attempt;
        });
        assertThat(result).isEqualTo("approved@2");
        assertThat(calls).hasValue(2);
    }
}
