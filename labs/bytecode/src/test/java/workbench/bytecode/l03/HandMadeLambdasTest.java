package workbench.bytecode.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodType;
import java.lang.reflect.Proxy;
import java.util.function.IntUnaryOperator;

import static org.assertj.core.api.Assertions.assertThat;

class HandMadeLambdasTest {

    @Test
    @DisplayName("adder() adds two numbers of seconds")
    void adderAdds() {
        assertThat(HandMadeLambdas.adder().applyAsInt(90, 30)).isEqualTo(120);
    }

    @Test
    @DisplayName("adder() is a hidden $$Lambda class, not a proxy, and the same object on every call")
    void adderIsALambda() {
        Object a = HandMadeLambdas.adder();
        assertThat(a.getClass().isHidden()).isTrue();
        assertThat(a.getClass().getName()).contains("$$Lambda");
        assertThat(Proxy.isProxyClass(a.getClass())).isFalse();
        assertThat(HandMadeLambdas.adder()).isSameAs(a);
    }

    @Test
    @DisplayName("plusDelay(delay) adds the captured delay to each cue time")
    void plusDelayCaptures() {
        assertThat(HandMadeLambdas.plusDelay(5).applyAsInt(90)).isEqualTo(95);
        assertThat(HandMadeLambdas.plusDelay(10).applyAsInt(90)).isEqualTo(100);
    }

    @Test
    @DisplayName("plusDelay: one linked call site, so two delays give two objects of ONE class")
    void plusDelayLinksOnce() {
        IntUnaryOperator d5 = HandMadeLambdas.plusDelay(5);
        IntUnaryOperator d10 = HandMadeLambdas.plusDelay(10);
        assertThat(d5).isNotSameAs(d10);
        assertThat(d5.getClass()).isSameAs(d10.getClass());
        assertThat(d5.getClass().isHidden()).isTrue();
    }

    @Test
    @DisplayName("lengthOf() is String::length behind the erased Function.apply, with the int boxed")
    void lengthOf() {
        assertThat(HandMadeLambdas.lengthOf().apply("Hamlet")).isEqualTo(6);
        assertThat(HandMadeLambdas.lengthOf().getClass().isHidden()).isTrue();
    }

    @Test
    @DisplayName("countdown() is a (long, String)String handle that fills the recipe")
    void countdown() throws Throwable {
        MethodHandle h = HandMadeLambdas.countdown();
        assertThat(h.type()).isEqualTo(MethodType.methodType(String.class, long.class, String.class));
        assertThat((String) h.invokeExact(90L, "thunder")).isEqualTo("90 seconds to thunder");
    }
}
