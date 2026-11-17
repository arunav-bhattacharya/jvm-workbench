package workbench.kotlin.l04;

import kotlin.Unit;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class OrderFromJavaTest {

    @Test
    @DisplayName("Java calls the DSL with a Function1<BookletBuilder, Unit>: the receiver is the first parameter")
    void javaPassesTheBuilderAsAParameter() {
        Booklet b = PrintOrderKt.printBooklet("menu", builder -> {
            builder.setNote("staple on the fold");
            builder.cover(4);
            builder.pages("dishes", 8);
            return Unit.INSTANCE;                      // a Kotlin () -> Unit returns Unit, so Java must too
        });
        assertThat(b.getParts()).hasSize(2);
        assertThat(b.getNote()).isEqualTo("staple on the fold");
    }
}
