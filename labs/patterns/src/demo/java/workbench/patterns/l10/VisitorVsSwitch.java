package workbench.patterns.l10;

/** The same expression tree evaluated with a classic Visitor and with a sealed switch. */
public class VisitorVsSwitch {
    interface ExprVisitor<R> { R visitNum(Num n); R visitAdd(Add a); R visitMul(Mul m); }

    sealed interface Expr permits Num, Add, Mul { <R> R accept(ExprVisitor<R> v); }
    record Num(int value) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitNum(this); } }
    record Add(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitAdd(this); } }
    record Mul(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitMul(this); } }

    // operation 1, visitor style: one class per operation, one method per case
    static final class Eval implements ExprVisitor<Integer> {
        public Integer visitNum(Num n) { return n.value(); }
        public Integer visitAdd(Add a) { return a.l().accept(this) + a.r().accept(this); }
        public Integer visitMul(Mul m) { return m.l().accept(this) * m.r().accept(this); }
    }

    // operation 1 again, data style: no accept needed, no visitor interface
    static int eval(Expr e) {
        return switch (e) {
            case Num(var v) -> v;
            case Add(var l, var r) -> eval(l) + eval(r);
            case Mul(Num(var z), var r) when z == 0 -> 0;     // nested record pattern: hard to say with a visitor
            case Mul(var l, var r) -> eval(l) * eval(r);
        };
    }

    // operation 2: just one more function
    static String show(Expr e) {
        return switch (e) {
            case Num(var v) -> Integer.toString(v);
            case Add(var l, var r) -> "(" + show(l) + " + " + show(r) + ")";
            case Mul(var l, var r) -> show(l) + " * " + show(r);
        };
    }

    public static void main(String[] args) {
        Expr e = new Add(new Num(2), new Mul(new Num(3), new Num(4)));
        System.out.println(show(e) + " = " + e.accept(new Eval()) + " (visitor) = " + eval(e) + " (switch)");
        Expr zero = new Mul(new Num(0), e);
        System.out.println(show(zero) + " = " + eval(zero));
    }
}
