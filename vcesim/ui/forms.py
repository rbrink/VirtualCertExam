from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, BooleanField, SubmitField, \
  PasswordField, TextAreaField, FieldList, FormField, Form as BaseForm
from wtforms.validators import DataRequired, Length, EqualTo, Email, \
  Optional, NumberRange, ValidationError


class LoginForm(FlaskForm):
    """
    VCESIM User Login form.
    This form is used on:
      - /login

    Fields:
        username (StringField): The user's username (required).
        password (PasswordField): The user's password (required).
        remember_me (BooleanField): Remember user
        submit (SubmitField): Button to submit the login form.
    """
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=12)])
    remember_me = BooleanField("Remember Me", default=False)
    submit = SubmitField("Login")

class RegisterStudent(FlaskForm):
    """
    VCESIM Register Student
    This form is used on:
      - /register

    Fields:
        username (StringField): The user's username (required).
        password (PasswordField): The user's password (required).
        confirm_pass (PasswordField): Confirm user's password (required).
        email (StringField): The user's email (required).
        first_name (StringField): The user's first name (required).
        last_name (StringField): The user's last name (required).
        course (StringField): user's current course (required)
        instructor (StringField): user's current instructor (required)
        role (StringField): Is user student or instructor/admin.
        submit (SubmitField): Button to submit registration.
    """
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    course = StringField("Course", validators=[DataRequired()])
    instructor = StringField("Instructor", validators=[DataRequired()])
    role = StringField("Role", default="student")
    submit = SubmitField("Sumbit")

class CreateExam(FlaskForm):
    """
    Create Exam form.
    The form is used on:
      - /exam_form.html (for instructors to create exams)
    
    Fields:
      title (StringField): Title of Exam
      exam_number (StringField): Number of Exam (i.e. N10-005)
      version (StringField): Exam Version
      passing_score (IntegerField): Score needed to pass exam
      time_limit (IntegerField): Exam time limit
      description (TextAreaField): Exam description
      submit (SubmitField): Button to save exam
    """
    title = StringField("Title", validators=[DataRequired()])
    exam_number = StringField("Exam Number", default="000-000")
    version = StringField("Exam Version", default="1.0")
    passing_score = IntegerField("Passing Score", default=800)
    time_limit = IntegerField("Time Limit (minutes)", default=120)
    description = TextAreaField("Description")
    submit = SubmitField("Save")
    
class OptionSubForm(BaseForm):
    """Subform for a single choice option (used inside a FieldList)."""
    text = StringField('Option Text', validators=[Optional()])
    is_correct = BooleanField('Correct', default=False)

class QuestionForm(FlaskForm):
    """Form for creating/editing a question with a fixed number of options.

    - Uses a FieldList of 4 OptionSubForm entries by default.
    - Performs cross-field validation (min options, at least one correct,
      single/multi-answer constraints).
    """
    question_text = TextAreaField("Question Text", validators=[DataRequired()])
    is_multianswer = BooleanField("Multi-Answer")
    options = FieldList(FormField(OptionSubForm), min_entries=4, max_entries=4)
    category = StringField("Category", validators=[Optional()])
    complexity = IntegerField("Complexity", default=1, validators=[NumberRange(min=1, max=10)])
    explanation = TextAreaField("Explanation", validators=[Optional()])
    submit = SubmitField("Save")

    def validate(self):
        """Run base validation then perform cross-field checks on options.

        Rules enforced:
          - At least two non-empty options.
          - At least one correct option.
          - If `is_multianswer` is False, only one correct option allowed.
        """
        rv = super().validate()
        if not rv:
            return False

        non_empty = [opt for opt in self.options.data if opt.get('text') and opt.get('text').strip()]
        if len(non_empty) < 2:
            self.options.errors.append('Please provide at least two options.')
            return False

        correct_count = sum(1 for opt in non_empty if opt.get('is_correct'))
        if correct_count == 0:
            self.options.errors.append('Please mark at least one option as correct.')
            return False

        if not self.is_multianswer.data and correct_count > 1:
            self.options.errors.append('Only one correct option allowed for single-answer questions.')
            return False

        return True
    
