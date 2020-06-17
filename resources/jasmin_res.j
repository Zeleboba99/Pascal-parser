.class public pr3
.super java/lang/Object
.field public static x I
.field public static y I
.field public static i I
.method public static Alpha(II)I
.limit stack 100
.limit locals 100
iload_1
iload_0
iadd
istore_0
iload_0
ireturn
.end method
.method                  public static main([Ljava/lang/String;)V
.limit stack          100
.limit locals         100

ldc 1
putstatic pr3/x I
getstatic pr3/x I
putstatic pr3/y I
getstatic pr3/y I
ldc 45
iadd
ldc 1
ldc 1
iadd
imul
putstatic pr3/y I
ldc 3
getstatic pr3/y I
iadd
ldc 1
isub
putstatic pr3/x I
getstatic             java/lang/System/out Ljava/io/PrintStream;
getstatic pr3/y I
invokevirtual         java/io/PrintStream/println(I)V
ldc 3
ldc 5
invokestatic pr3/Alpha(II)I
putstatic pr3/y I
while_0:
getstatic pr3/y I
ldc 100
swap
if_icmplt done_0
getstatic             java/lang/System/out Ljava/io/PrintStream;
getstatic pr3/y I
invokevirtual         java/io/PrintStream/println(I)V
getstatic pr3/y I
ldc 1
iadd
putstatic pr3/y I
getstatic             java/lang/System/out Ljava/io/PrintStream;
getstatic pr3/y I
invokevirtual         java/io/PrintStream/println(I)V
goto while_0
done_0:
getstatic pr3/y I
ldc 1
swap
if_icmpgt else_1
ldc 1
putstatic pr3/x I
goto endif_1
else_1:
ldc 2
putstatic pr3/x I
endif_1:
   return
.end method