package workbench.performance.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class DocumentGuardsTest {
    private static final int MAX_INLINE_SIZE = 35;   // C2's limit at call sites it doesn't consider hot

    @Test
    @DisplayName("requireWordCount fits in 35 bytes of bytecode, so C2 can inline it at any call site")
    void requireWordCountIsSmall() throws Exception {
        int size = BytecodeSize.of(DocumentGuards.class, "requireWordCount", "(J)J");
        assertThat(size).as("bytecode size of requireWordCount").isLessThanOrEqualTo(MAX_INLINE_SIZE);
    }

    @Test
    @DisplayName("requireTitle fits in 35 bytes of bytecode")
    void requireTitleIsSmall() throws Exception {
        int size = BytecodeSize.of(DocumentGuards.class, "requireTitle", "(Ljava/lang/String;)Ljava/lang/String;");
        assertThat(size).as("bytecode size of requireTitle").isLessThanOrEqualTo(MAX_INLINE_SIZE);
    }

    @Test
    @DisplayName("requireWordCount still returns valid counts and rejects bad ones with the same message")
    void requireWordCountBehaves() {
        assertThat(DocumentGuards.requireWordCount(1)).isEqualTo(1);
        assertThat(DocumentGuards.requireWordCount(10_000_000)).isEqualTo(10_000_000);
        assertThatThrownBy(() -> DocumentGuards.requireWordCount(0))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("word count must be between 1 and 10000000, got 0");
        assertThatThrownBy(() -> DocumentGuards.requireWordCount(10_000_001))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("word count must be between 1 and 10000000, got 10000001");
    }

    @Test
    @DisplayName("requireTitle still returns valid titles and rejects bad ones with the same message")
    void requireTitleBehaves() {
        assertThat(DocumentGuards.requireTitle("A")).isEqualTo("A");
        String max = "a".repeat(64);
        assertThat(DocumentGuards.requireTitle(max)).isSameAs(max);
        assertThatThrownBy(() -> DocumentGuards.requireTitle(null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("title must be 1 to 64 characters, got null");
        assertThatThrownBy(() -> DocumentGuards.requireTitle(""))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("title must be 1 to 64 characters, got 0");
        assertThatThrownBy(() -> DocumentGuards.requireTitle("a".repeat(65)))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("title must be 1 to 64 characters, got 65");
    }
}
