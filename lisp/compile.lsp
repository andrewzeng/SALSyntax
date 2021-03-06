(defun sal-compiler (filename &key verbose print)
  (let ((input "") (file (open filename)) line lines)
    (cond (file
           (push filename *loadingfiles*)
           (while (setf line (read-line file))
            (push line lines)
            (push "\n" lines))
           (close file)
           (setf input (strcat-list (reverse lines)))
           (sal-trace-enter (strcat "Loading " filename))
           (sal-compile input f t filename)
           (pop *loadingfiles*)
           (sal-trace-exit))
          (t
           (format t "error loading SAL file ~A~%" filename)))))

(sal-load {SAL_FILE})

(print "SUBLIME.SENTINEL")