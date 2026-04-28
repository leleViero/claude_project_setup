## Creating Gabbar Singh: Unit Test Reviewer Agent

The BMB create-agent workflow will build our Gabbar Singh unit test reviewer agent through an interactive, multi-step process that transforms the iconic character’s personality into a specialized testing assistant

## The Workflow Engine

workflow.yaml is the configuration file that defines:

-   The workflow’s metadata and paths
-   Where to find instructions and documentation
-   Output locations for the generated agent

The actual execution logic lives in **instructions.md**, which uses XML tags to define each step of the agent creation process

## Optional Brainstorming (Step -1)

The workflow starts with an optional brainstorming phase

```
<step n="-1" goal="Optional brainstorming for agent ideas" optional="true">  
  <ask>Do you want to brainstorm agent ideas first? [y/n]</ask>  
    
  <check if="user answered yes">  
    <action>Invoke brainstorming workflow: {project-root}/bmad/core/workflows/brainstorming/workflow.yaml</action>  
    <action>Pass context data: {installed_path}/brainstorm-context.md</action>  
    <action>Wait for brainstorming session completion</action>  
    <action>Use brainstorming output to inform agent identity and persona development in following steps</action>  
  </check>  
</step>
```

## The Brainstorming Context File

brainstorm-context.md provides focused guidance for the brainstorming workflow . For Gabbar Singh, this would help explore:

-   How his iconic dialogue style (“Kitne aadmi the?”) could frame test coverage questions
-   His menacing yet fair approach to code review
-   Specific testing commands he might execute

## Using Brainstorming Output

After brainstorming completes, Step 1 references those results to guide the conversation . The output informs:

-   Agent type (likely Expert for domain-specific testing knowledge)
-   Personality traits (authoritative, thorough, memorable catchphrases)
-   Command ideas (\*review-tests, \*coverage-report, \*mock-analysis)

## Agent Creation Phases

The workflow continues through structured phases :

1.  Agent Setup: Determine if Gabbar should be Simple, Expert, or Module agent
2.  Persona Development: Define his role as “Unit Test Reviewer” with Sholay-inspired identity
3.  Command Building: Create testing-specific commands with his signature style
4.  Finalization: Generate the complete `.agent.yaml` file

## Final Output

The workflow generates the complete YAML file

```
agent:  
  metadata:  
    id: bmad/agents/gabbar-singh.md  
    name: Gabbar Singh  
    title: Unit Test Reviewer  
    icon: 🎭  
    module: custom  
  persona:  
    role: 'Fearless enforcer of test coverage and quality'  
    identity: 'Legendary dacoit turned code guardian, demanding complete test coverage with his iconic intensity...'  
    communication_style: 'Speaks in memorable Sholay dialogues, demanding thorough testing...'  
  menu:  
    - trigger: review-tests  
      workflow: "{project-root}/custom/workflows/review-tests/workflow.yaml"  
      description: "Review unit tests with Gabbar's critical eye"
```

and then once its ready you can activate the agent

## Gabbar Singh Unit Test Review Examples

Here’s how your Gabbar Singh agent would review unit tests with his iconic Sholay-style personality:

## Example 1: Reviewing Incomplete Test Coverage

User submits: `UserService.test.js` with only happy path tests

````
🎭 "Arre o Sambha! Kitne tests hain? *Kitne aadmi the?*"  
  
I see only 2 tests for UserService, but there are 5 branches in your validateEmail() function!  
You're testing the happy path, but what about:  
- Invalid email formats?   
- Null inputs?  
- Edge cases like empty strings?  
  
**Missing coverage: 60%** - This is not acceptable! Add tests for these branches or I'll... *compile your code with my bare hands!*  
  
Suggested additions:  
```javascript  
test('should reject null email', () => {  
  expect(() => userService.validateEmail(null)).toThrow('Email required');  
});  
  
test('should reject invalid formats', () => {  
  expect(userService.validateEmail('not-an-email')).toBe(false);  
});  
````

## Sharing Your Gabbar Singh Agent

Now we have several options to share our custom Gabbar Singh agent, from simple file sharing to creating a distributable module.

## Option 1: Share Source Files ( Simple)

Share the agent’s source files directly:

```
gabbar-singh-agent/  
├── gabbar-singh.agent.yaml          
├── _sidecar/                        
│   ├── private-instructions.md  
│   └── knowledge/  
└── README.md                        
```

The recipient can:

1.  Copy `gabbar-singh.agent.yaml` to their `bmad/agents/` directory
2.  Run `npx bmad-method@alpha install` and select "Compile Agents"

## Option 2: Create a Shareable Module

Package your agent as a BMAD module for proper distribution module- :

```
gabbar-test-reviewer/  
├── agents/  
│   └── gabbar-singh.agent.yaml  
├── workflows/                       
│   ├── review-tests/  
│   └── coverage-analysis/  
├── _module-installer/  
│   └── install-config.yaml  
└── README.md
```

Use BMB’s `create-module` workflow to generate this structure .

## Option 3: Web Bundle Distribution

Create a self-contained web bundle for online sharing web-bundler-usage.md:5–6 :

```

node tools/cli/bundlers/bundle-web.js agent custom gabbar-singh
```

This generates `web-bundles/custom/agents/gabbar-singh.xml` - a standalone file with all dependencies embedded .

## Option 4: Share Compiled Agent

Share the compiled `.md` file for immediate IDE use:

1.  After compiling, find the agent at `bmad/agents/gabbar-singh.md`
2.  Share this file — recipients can copy it directly to their IDE’s agent directory

## Recommended Approach

For sharing Gabbar Singh, I recommend Option 2 (Create a Module) because it:

-   Provides proper installation via `npx bmad-method@alpha install --source /path/to/module`
-   Includes any custom workflows for test review
-   Supports future updates and customization
-   Follows BMAD’s distribution standards

## Custom Agent ON Antigravity

Start the workflow

Select the Create Agent Menu

Provide Exact Agent Behaviour

When we type `@gabbar-singh`, our IDE activates the compiled agent file located at `bmad/custom/agents/gabbar-singh.md` . The `.bmad custom gabbar-singh` path we are referring to is the source location where our YAML definition lives: `bmad/custom/agents/gabbar-singh.agent.yaml`

## How Activation Works by IDE

## Cline

1.  Toggle Rule: Enable the agent in `.clinerules/`
2.  Activate: Type `@gabbar-singh` in chat
3.  Agent loads: The compiled `.md` file provides the XML persona and menu

## iFlow

1.  Navigate: Browse to `.iflow/commands/bmad/agents/`
2.  Select: Choose the gabbar-singh command
3.  Execute: Agent activates for session

## Other IDEs

Each IDE handles activation differently but always uses the compiled `.md` file from `bmad/custom/agents/`

Building the Gabbar Singh unit test reviewer showed how flexible and practical the BMB toolkit can be. With a structured workflow and clear design steps, it becomes surprisingly simple to turn a character idea, a testing requirement, or even a personal creative spark into a working agent inside the BMAD ecosystem. The process keeps the developer in control while the framework handles the repetitive and structural parts.

As you continue exploring BMAD, this approach opens the door to many more possibilities — specialized reviewers, debugging helpers, creative companions, or full modules that fit your own style of development. Gabbar Singh is just one example of how technical utility and personality can come together to create agents that are both useful and fun to work with.